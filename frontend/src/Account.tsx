import { useEffect, useRef, useState } from 'react';
import { createClient, type User } from '@supabase/supabase-js';

const env = (import.meta as ImportMeta & { env: Record<string, string> }).env;
const url = env.VITE_SUPABASE_URL;
const key = env.VITE_SUPABASE_PUBLISHABLE_KEY;
const auth = url && key ? createClient(url, key, { auth: { flowType: 'pkce' } }).auth : null;

export function Account() {
    const [user, setUser] = useState<User | null>(null);
    const [mode, setMode] = useState<'signin' | 'signup'>('signin');
    const [email, setEmail] = useState('');
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const dialog = useRef<HTMLDialogElement>(null);
    useEffect(() => {
        if (!auth) return;
        let active = true;
        auth.getSession().then(({ data, error }) => {
            if (!active) return;
            setUser(data.session?.user ?? null);
            if (error) { setError('Your sign-in link could not be completed. Please request a new one.'); dialog.current?.showModal(); }
        });
        const { data } = auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null);
            if (session) dialog.current?.close();
        });
        return () => { active = false; data.subscription.unsubscribe(); };
    }, []);
    const open = (next: 'signin' | 'signup') => { setMode(next); setMessage(''); setError(''); dialog.current?.showModal(); };
    async function provider(provider: 'google' | 'github') {
        if (!auth) return;
        setBusy(true); setError('');
        try {
            const { error } = await auth.signInWithOAuth({ provider, options: { redirectTo: window.location.origin + '/' } });
            if (error) throw error;
        } catch { setError('Unable to connect to this provider. Please try email or try again later.'); }
        finally { setBusy(false); }
    }
    function emailLink(event: React.FormEvent) {
        event.preventDefault();
        setError('');
        setMessage('Coming soon! Email sign-in is on the way. You can explore Standora without an account in the meantime.');
    }
    async function signOut() {
        if (!auth) return;
        setBusy(true);
        const { error } = await auth.signOut();
        setBusy(false);
        if (error) { setError('Unable to sign out. Please try again.'); dialog.current?.showModal(); }
    }
    return <><div className="auth-actions">{user ? <><span className="account-user" title={user.email}>{user.email}</span><button disabled={busy} className="auth-signin" onClick={signOut}>Sign out</button></> : <><button className="auth-signin" onClick={() => open('signin')}>Sign in</button><button className="auth-signup" onClick={() => open('signup')}>Sign up</button></>}</div>
        <dialog ref={dialog} className="auth-dialog" aria-labelledby="auth-title">
            <button className="auth-close" aria-label="Close account window" onClick={() => dialog.current?.close()}>×</button>
            <span className="eyebrow">YOUR STANDORA ACCOUNT</span>
            <h2 id="auth-title">{mode === 'signup' ? 'Welcome to Standora' : 'Welcome back'}</h2>
            <p>Find where your business belongs.</p>
            {!auth && <p className="auth-feedback" role="status">Account access is being set up. Please check back soon.</p>}
            <div className="auth-providers"><button disabled={!auth || busy} onClick={() => provider('google')}>Continue with Google</button><button disabled={!auth || busy} onClick={() => provider('github')}>Continue with GitHub</button></div>
            <div className="auth-divider">or use your email</div>
            <form onSubmit={emailLink}><label>Email address<input type="email" autoComplete="email" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" disabled={busy}/></label><button className="primary" disabled={busy}>{busy ? 'Connecting…' : mode === 'signup' ? 'Sign up' : 'Sign in'}</button></form>
            <p className="auth-note">Email access is coming soon. Your address won’t be sent or saved.</p>
            {message && <p className="auth-feedback" role="status">{message}</p>}{error && <p className="auth-feedback" role="alert">{error}</p>}
            <button className="text-button" onClick={() => { setMode(mode === 'signup' ? 'signin' : 'signup'); setError(''); setMessage(''); }}>{mode === 'signup' ? 'Already have an account? Sign in' : 'New to Standora? Sign up'}</button>
        </dialog></>;
}
