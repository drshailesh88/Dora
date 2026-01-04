"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Search,
  Pill,
  History,
  Settings,
  CreditCard,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Query", href: "/query", icon: Search },
  { name: "Drug Interactions", href: "/drugs", icon: Pill },
  { name: "History", href: "/history", icon: History },
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Subscription", href: "/pricing", icon: CreditCard },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-white dark:bg-gray-900 border-r">
      <div className="flex h-16 items-center justify-center border-b px-6">
        <Link href="/dashboard" className="text-2xl font-bold text-primary">
          Dora
        </Link>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-white"
                  : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
