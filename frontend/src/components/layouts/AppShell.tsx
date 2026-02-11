"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, currentOrg, organizations, isAuthenticated, isLoading, logout, switchOrganization } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);
  const [orgMenuOpen, setOrgMenuOpen] = React.useState(false);

  // Redirect to login if not authenticated
  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Close menus when clicking outside
  React.useEffect(() => {
    const handleClick = () => {
      setUserMenuOpen(false);
      setOrgMenuOpen(false);
    };
    if (userMenuOpen || orgMenuOpen) {
      document.addEventListener("click", handleClick);
      return () => document.removeEventListener("click", handleClick);
    }
  }, [userMenuOpen, orgMenuOpen]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-25 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg mx-auto mb-4 animate-pulse">
            <span className="text-2xl">🐝</span>
          </div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  const navigation = [
    { name: "Dashboard", href: "/" },
    { name: "Leases", href: "/leases" },
    { name: "Analytics", href: "/analytics" },
    { name: "Examples", href: "/settings/examples" },
    { name: "Prompts", href: "/settings/prompts" },
  ];

  return (
    <div className="min-h-screen bg-slate-25">
      {/* Top Navigation */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Logo and Org Switcher */}
            <div className="flex items-center gap-6">
              <Link href="/" className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-sm">
                  <span className="text-xl">🐝</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
                    LeaseBee
                  </h1>
                  <p className="text-xs text-slate-500 -mt-0.5">
                    AI-Powered Lease Abstraction
                  </p>
                </div>
              </Link>

              {/* Organization Switcher */}
              {organizations.length > 0 && (
                <div className="hidden lg:block relative">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setOrgMenuOpen(!orgMenuOpen);
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-sm text-slate-600 transition-colors"
                  >
                    <span className="font-medium truncate max-w-[200px]">
                      {currentOrg?.name || 'Select Organization'}
                    </span>
                    <svg
                      className="w-4 h-4 text-slate-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </button>

                  {/* Organization Dropdown */}
                  {orgMenuOpen && (
                    <div className="absolute left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-slate-200 py-1 animate-slide-in z-50">
                      <div className="px-3 py-2 border-b border-slate-100">
                        <p className="text-xs font-medium text-slate-500 uppercase">
                          Organizations
                        </p>
                      </div>
                      <div className="py-1 max-h-64 overflow-y-auto">
                        {organizations.map((membership) => (
                          <button
                            key={membership.organization.id}
                            onClick={() => {
                              switchOrganization(membership.organization.id);
                              setOrgMenuOpen(false);
                            }}
                            className={cn(
                              "w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-slate-50 transition-colors",
                              currentOrg?.id === membership.organization.id && "bg-amber-50"
                            )}
                          >
                            <div className="flex-1 text-left">
                              <p className="font-medium text-slate-900">
                                {membership.organization.name}
                              </p>
                              <p className="text-xs text-slate-500">
                                {membership.role}
                              </p>
                            </div>
                            {currentOrg?.id === membership.organization.id && (
                              <svg
                                className="w-4 h-4 text-amber-600"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                      isActive
                        ? "bg-amber-50 text-amber-700"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    )}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setUserMenuOpen(!userMenuOpen);
                }}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                <Avatar
                  size="default"
                  fallback={user?.name?.[0] || 'U'}
                  alt={user?.name || 'User'}
                />
              </button>

              {/* User Menu Dropdown */}
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-1 animate-slide-in z-50">
                  <div className="px-4 py-2 border-b border-slate-100">
                    <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <div className="py-1">
                    <Link
                      href="/settings/account"
                      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      Profile Settings
                    </Link>
                    {currentOrg && organizations.find(o => o.organization.id === currentOrg.id)?.role === 'ADMIN' && (
                      <Link
                        href="/settings/team"
                        className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                      >
                        Team Management
                      </Link>
                    )}
                    <Link
                      href="/settings/billing"
                      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      Billing
                    </Link>
                    <Link
                      href="/help"
                      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      Help
                    </Link>
                  </div>
                  <div className="border-t border-slate-100 py-1">
                    <button
                      onClick={() => {
                        logout();
                        setUserMenuOpen(false);
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
