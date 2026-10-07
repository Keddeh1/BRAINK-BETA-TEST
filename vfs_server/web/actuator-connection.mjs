// Server-side actuator connection. The secret is never embedded in published HTML.
const hex = bytes => [...bytes].map(value => value.toString(16).padStart(2,"0")).join("");
const unhex = value => new Uint8Array(value.match(/../g).map(pair => parseInt(pair,16)));
const bytes = value => new TextEncoder().encode(value);
export class VFSActuatorConnection {
  constructor({surfaceId,secretHex,clock=()=>Math.floor(Date.now()/1000),random=crypto.getRandomValues.bind(crypto)}) {
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}$/.test(surfaceId) ||
        !/^[0-9a-f]{64}$/.test(secretHex)) throw new Error("VFS_ACTUATOR_CREDENTIAL_INVALID");
    this.surfaceId=surfaceId;this.secretHex=secretHex;this.clock=clock;this.random=random;
  }
  async headers({method,path,body,command}) {
    if (!["ab.admit","ab.observe"].includes(command) || method!=="POST" || !path.startsWith("/vfs/") ||
        typeof body!=="string") throw new Error("VFS_ACTUATOR_COMMAND_INVALID");
    const nonce=hex(this.random(new Uint8Array(16)));
    const time=String(this.clock());
    const digest=hex(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes(body))));
    const message=[method,path,this.surfaceId,digest,time,nonce,command].join("|");
    const key=await crypto.subtle.importKey("raw",unhex(this.secretHex),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
    const signature=hex(new Uint8Array(await crypto.subtle.sign("HMAC",key,bytes(message))));
    return {"x-vfs-surface":this.surfaceId,"x-vfs-time":time,
      "x-vfs-nonce":nonce,"x-vfs-signature":signature};
  }
}
