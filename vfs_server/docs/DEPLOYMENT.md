# VFS_SERVER production deployment gate

1. freeze exact Git commit;
2. compile and run unit qualification;
3. run `python -m vfs_server.qualification`;
4. build immutable container image and record digest;
5. provision persistent storage and mutation credential;
6. deploy with non-root user and read-only root filesystem;
7. wait for `/ready`;
8. write a qualification artifact;
9. perform OBSERVER readback;
10. restart the service;
11. repeat path, digest, lineage and receipt-chain readback;
12. record deployment evidence before routing production mutation traffic.

A repository push, container build, process start, HTTP 200, or actor receipt is not by itself a production deployment PASS.
