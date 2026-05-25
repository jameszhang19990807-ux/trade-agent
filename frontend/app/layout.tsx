'use client';

import './globals.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Overview', icon: 'Gauge' },
  { href: '/conversations', label: 'Conversations', icon: 'MessageSquare' },
  { href: '/pipeline', label: 'Pipeline', icon: 'Kanban' },
  { href: '/customers', label: 'Customers', icon: 'Users' },
  { href: '/settings', label: 'Settings', icon: 'Settings' },
];

function NavIcon({ name, className }: { name: string; className?: string }) {
  const s = { width: 18, height: 18, stroke: 'currentColor', fill: 'none', strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  switch (name) {
    case 'Gauge':
      return <svg {...s} className={className} viewBox="0 0 24 24"><path d="M12 2v3m0 14v3M4.93 4.93l2.12 2.12m9.9 9.9l2.12 2.12M2 12h3m14 0h3M4.93 19.07l2.12-2.12m9.9-9.9l2.12-2.12"/><circle cx="12" cy="12" r="7"/></svg>;
    case 'MessageSquare':
      return <svg {...s} className={className} viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
    case 'Kanban':
      return <svg {...s} className={className} viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="11" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="18" width="7" height="3" rx="1"/></svg>;
    case 'Users':
      return <svg {...s} className={className} viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
    case 'Settings':
      return <svg {...s} className={className} viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>;
    default: return null;
  }
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en">
      <body>
        <aside className="sidebar">
          <div className="sidebar-logo">
            <span>Trade</span>Agent
          </div>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`sidebar-link ${pathname === item.href ? 'active' : ''}`}
              >
                <NavIcon name={item.icon} />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </aside>
        <main className="main-content">
          {children}
        </main>
      </body>
    </html>
  );
}
