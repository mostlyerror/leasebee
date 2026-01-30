import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "error" | "warning" | "info" | "secondary";
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
          {
            "bg-slate-100 text-slate-700": variant === "default",
            "bg-green-100 text-green-700": variant === "success",
            "bg-red-100 text-red-700": variant === "error",
            "bg-orange-100 text-orange-700": variant === "warning",
            "bg-blue-100 text-blue-700": variant === "info",
            "bg-slate-100 text-slate-600": variant === "secondary",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Badge.displayName = "Badge";

export { Badge };
