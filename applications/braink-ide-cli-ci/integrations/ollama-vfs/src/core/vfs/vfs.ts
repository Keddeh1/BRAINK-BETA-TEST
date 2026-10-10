/**
 * VFS Primitive Implementation
 * 
 * Complexity Analysis:
 * - CRUD: O(1) for direct inode access, O(log N) for path lookup (where N is depth)
 * 
 * Safety Constraints:
 * - Atomic operation locks (Semaphore-based)
 * - Persistent backing storage via IndexedDB
 */

import { z } from 'zod';
import { InodeId, brandInodeId } from '../types';
import { VFS_STORAGE_INDEXED_DB } from '../../services/vfsStorageIndexedDb';

const InodeSchema = z.object({
  id: z.string(),
  metadata: z.record(z.string(), z.any()),
  data: z.any(),
});

export class VFSPrimitive {
  private inodes: Map<InodeId, z.infer<typeof InodeSchema>> = new Map();
  private locks: Set<InodeId> = new Set();
  private isHydrated = false;

  private async acquireLock(id: InodeId): Promise<void> {
    while (this.locks.has(id)) {
      await new Promise(resolve => setTimeout(resolve, 1));
    }
    this.locks.add(id);
  }

  private releaseLock(id: InodeId): void {
    this.locks.delete(id);
  }

  /**
   * Hydrate in-memory inodes from IndexedDB persistent store
   */
  async hydrateFromIndexedDb(): Promise<void> {
    try {
      const persistedInodes = await VFS_STORAGE_INDEXED_DB.getAllInodes();
      for (const record of persistedInodes) {
        const brandedId = brandInodeId(record.id);
        this.inodes.set(brandedId, {
          id: record.id,
          metadata: record.metadata || {},
          data: record.data,
        });
      }
      this.isHydrated = true;
      console.log(`[VFSPrimitive] Hydrated ${persistedInodes.length} persistent inodes.`);
    } catch (err) {
      console.warn('[VFSPrimitive] Could not hydrate from IndexedDB, operating in-memory:', err);
    }
  }

  async create(id: string, metadata: Record<string, any>, data: any): Promise<void> {
    const brandedId = brandInodeId(id);
    const validated = InodeSchema.parse({ id, metadata, data });
    
    await this.acquireLock(brandedId);
    try {
      if (this.inodes.has(brandedId)) throw new Error(`Inode already exists: ${id}`);
      // Commit backing storage before publishing the new inode.
      await VFS_STORAGE_INDEXED_DB.saveInode({
        id,
        path: metadata.path,
        metadata,
        data,
        updatedAt: new Date().toISOString()
      });
      this.inodes.set(brandedId, validated);
    } finally {
      this.releaseLock(brandedId);
    }
  }

  async read(id: string): Promise<z.infer<typeof InodeSchema>> {
    const brandedId = brandInodeId(id);
    await this.acquireLock(brandedId);
    try {
      let inode = this.inodes.get(brandedId);
      if (!inode) {
        // Attempt lazy load from IndexedDB
        const persisted = await VFS_STORAGE_INDEXED_DB.getInode(id);
        if (persisted) {
          inode = {
            id: persisted.id,
            metadata: persisted.metadata,
            data: persisted.data
          };
          this.inodes.set(brandedId, inode);
        }
      }
      if (!inode) throw new Error(`Inode not found: ${id}`);
      return InodeSchema.parse(inode);
    } finally {
      this.releaseLock(brandedId);
    }
  }

  async update(id: string, metadata: Record<string, any>, data: any): Promise<void> {
    const brandedId = brandInodeId(id);
    const validated = InodeSchema.parse({ id, metadata, data });
    
    await this.acquireLock(brandedId);
    try {
      if (!this.inodes.has(brandedId)) throw new Error(`Inode not found: ${id}`);
      // Commit backing storage before publishing the new inode.
      await VFS_STORAGE_INDEXED_DB.saveInode({
        id,
        path: metadata.path,
        metadata,
        data,
        updatedAt: new Date().toISOString()
      });
      this.inodes.set(brandedId, validated);
    } finally {
      this.releaseLock(brandedId);
    }
  }

  async delete(id: string): Promise<void> {
    const brandedId = brandInodeId(id);
    await this.acquireLock(brandedId);
    try {
      if (!this.inodes.has(brandedId)) throw new Error(`Inode not found: ${id}`);
      await VFS_STORAGE_INDEXED_DB.deleteInode(id);
      this.inodes.delete(brandedId);
    } finally {
      this.releaseLock(brandedId);
    }
  }

  async flushToIndexedDb(): Promise<void> {
    for (const [id, inode] of this.inodes.entries()) {
      await VFS_STORAGE_INDEXED_DB.saveInode({
        id: inode.id,
        path: inode.metadata.path,
        metadata: inode.metadata,
        data: inode.data,
        updatedAt: new Date().toISOString()
      });
    }
  }
}

export const GLOBAL_VFS_PRIMITIVE = new VFSPrimitive();
