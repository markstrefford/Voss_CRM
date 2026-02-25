import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import {
  LayoutDashboard, Users, Building2, Handshake, KanbanSquare,
  Clock, LogOut, Menu,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/contacts', label: 'Contacts', icon: Users },
  { to: '/companies', label: 'Companies', icon: Building2 },
  { to: '/deals', label: 'Deals', icon: Handshake },
  { to: '/pipeline', label: 'Pipeline', icon: KanbanSquare },
  { to: '/follow-ups', label: 'Follow-ups', icon: Clock },
];

function NavContent({ onClose }: { onClose?: () => void }) {
  const location = useLocation();
  const { logout, user } = useAuth();

  return (
    <div className="flex h-full flex-col">
      <div className="p-4 border-b">
        <h1 className="text-lg font-bold">Voss</h1>
        {user && <p className="text-sm text-muted-foreground">{user.username}</p>}
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            onClick={onClose}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
              location.pathname === to
                ? 'bg-accent text-accent-foreground font-medium'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
      <div className="p-2 border-t">
        <Button variant="ghost" className="w-full justify-start gap-3" onClick={logout}>
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-56 flex-col border-r bg-sidebar">
        <NavContent />
      </aside>

      {/* Mobile header + sheet */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="md:hidden flex items-center gap-2 border-b px-4 py-3">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-56 p-0">
              <NavContent onClose={() => setOpen(false)} />
            </SheetContent>
          </Sheet>
          <h1 className="text-lg font-bold">Voss</h1>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
