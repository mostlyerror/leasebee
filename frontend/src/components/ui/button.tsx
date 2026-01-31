import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "secondary" | "ghost" | "destructive" | "outline";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-lg text-base font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
          {
            // Primary: Amber brand button
            "bg-amber-500 text-white hover:bg-amber-600 active:bg-amber-700 shadow-sm hover:shadow":
              variant === "default" || variant === "primary",
            // Secondary: Slate button
            "bg-slate-100 text-slate-700 hover:bg-slate-200 active:bg-slate-300":
              variant === "secondary",
            // Ghost: Transparent with hover
            "hover:bg-slate-100 hover:text-slate-900 text-slate-600":
              variant === "ghost",
            // Destructive: Red error button
            "bg-red-500 text-white hover:bg-red-600 active:bg-red-700 shadow-sm":
              variant === "destructive",
            // Outline: Border with transparent bg
            "border-2 border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:border-slate-300":
              variant === "outline",
          },
          {
            "h-10 px-4 py-2": size === "default",
            "h-9 px-3 text-sm": size === "sm",
            "h-11 px-8 text-lg": size === "lg",
            "h-10 w-10 p-0": size === "icon",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
