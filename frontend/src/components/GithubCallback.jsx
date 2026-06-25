import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function GithubCallback({ setIsAuthenticated, onTokenReceived }) {
    const [status, setStatus] = useState("> Initializing OAuth 2.0 callback handler...");
    const [isError, setIsError] = useState(false);

    const hasFetched = useRef(false);

    useEffect(() => {
        const authenticate = async () => {
            if (hasFetched.current) return;

            const params = new URLSearchParams(window.location.search);
            const code = params.get('code');

            const githubError = params.get('error');
            const errorDescription = params.get('error_description');

            if (githubError) {
                setIsError(true);
                setStatus(`> [GITHUB ERROR] ${errorDescription || githubError}`);
                return;
            }

            if (!code) {
                setIsError(true);
                setStatus("> [ERROR] No authorization code found in URL parameters. Did you start from the login button?");
                return;
            }

            hasFetched.current = true;

            try {
                setStatus("> Authenticating with GitHub...");

                await new Promise(res => setTimeout(res, 800));
                setStatus("> Exchanging authorization code for secure access token...");

                const response = await fetch(`${API_BASE}/api/auth/github`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ code })
                });

                if (!response.ok) {
                    const errorPayload = await response.json();
                    throw new Error(errorPayload.detail || `Server returned status ${response.status}`);
                }

                const data = await response.json();
                const accessToken = data.access_token;

                if (onTokenReceived) {
                    onTokenReceived(accessToken);
                }

                await new Promise(res => setTimeout(res, 600));
                setStatus("> Synchronizing pipeline access capabilities...");

                await new Promise(res => setTimeout(res, 500));
                setStatus("> Authentication successful! Booting SmartTIA Engine...");

                setTimeout(() => {
                    setIsAuthenticated(true);
                    window.history.replaceState({}, document.title, '/');
                }, 1200);

            } catch (error) {
                console.error("Authentication Pipeline Error:", error);
                setIsError(true);
                setStatus(`> [FATAL] Handshake failed: ${error.message}`);
            }
        };

        authenticate();
    }, [setIsAuthenticated, onTokenReceived]);

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 w-full font-sans">
            <div className="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
                {/* Terminal Window Header */}
                <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-slate-400" />
                    <span className="text-xs text-slate-500 font-mono">auth_handshake.sh</span>
                </div>

                {/* Terminal Window Body */}
                <div className="p-6 md:p-8 font-mono text-sm space-y-3 min-h-[160px]">
                    <div className={`${isError ? 'text-red-400' : 'text-emerald-400'} transition-colors duration-300`}>
                        {status}
                    </div>
                    {!isError && <div className="text-slate-500 animate-pulse">_</div>}
                </div>
            </div>
        </div>
    );
}