import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ className, icon, title, description, action, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center justify-center py-12 px-4 text-center",
          className
        )}
        {...props}
      >
        {icon && (
          <div className="mb-4 text-slate-400">
            {icon}
          </div>
        )}
        <h3 className="text-lg font-semibold text-slate-900 mb-2">
          {title}
        </h3>
        {description && (
          <p className="text-sm text-slate-500 mb-6 max-w-md">
            {description}
          </p>
        )}
        {action && (
          <Button onClick={action.onClick} variant="primary">
            {action.label}
          </Button>
        )}
      </div>
    );
  }
);
EmptyState.displayName = "EmptyState";

export { EmptyState };
