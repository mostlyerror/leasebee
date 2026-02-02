import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <select
        className={cn(
          "flex h-10 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm",
          "focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-slate-50",
          "transition-colors cursor-pointer",
          className
        )}
        ref={ref}
        {...props}
      >
        {children}
      </select>
    );
  }
);
Select.displayName = "Select";

export { Select };
