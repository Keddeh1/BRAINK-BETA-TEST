import {headers} from 'next/headers';
import {authorizeOperations} from '@/lib/20260927T0036Z__KEDDEH-COM__BRAINK__ACCESS';
import {chatGPTSignInPath} from '../chatgpt-auth';
import Workspace from '@/components/workspace/workspace';
export const dynamic='force-dynamic';
export default async function Page(){
 const status=authorizeOperations(new Headers(await headers()));
 if(status!==200)return <main className="min-h-screen bg-[#070a0f] text-slate-100 p-8"><p className="text-emerald-300">KEDDEH SYSTEMS</p><h1 className="text-3xl my-8">Runtime workspace</h1><p className="mb-8">{status===403?'This account does not have operator access.':'Sign in to access your runtime workspace.'}</p><a className="bg-emerald-300 text-black px-5 py-3" href={chatGPTSignInPath('/workspace')} target="_top">Sign in</a><a className="ml-6 underline" href="/">Control plane</a></main>;
 return <Workspace/>;
}
