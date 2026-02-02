import * as React from "react";
import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

export interface StatsCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  change?: {
    value: string;
    trend: "up" | "down" | "neutral";
  };
  icon?: React.ReactNode;
}

const StatsCard = React.forwardRef<HTMLDivElement, StatsCardProps>(
  ({ className, title, value, change, icon, ...props }, ref) => {
    return (
      <Card
        ref={ref}
        className={cn("p-6", className)}
        {...props}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-600 mb-1">
              {title}
            </p>
            <p className="text-3xl font-bold text-slate-900">
              {value}
            </p>
            {change && (
              <div className="flex items-center gap-1 mt-2">
                {change.trend === "up" && (
                  <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                )}
                {change.trend === "down" && (
                  <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
                <span className={cn(
                  "text-sm font-medium",
                  change.trend === "up" && "text-green-600",
                  change.trend === "down" && "text-red-600",
                  change.trend === "neutral" && "text-slate-600"
                )}>
                  {change.value}
                </span>
              </div>
            )}
          </div>
          {icon && (
            <div className="p-3 bg-amber-50 rounded-lg text-amber-600">
              {icon}
            </div>
          )}
        </div>
      </Card>
    );
  }
);
StatsCard.displayName = "StatsCard";

export { StatsCard };
