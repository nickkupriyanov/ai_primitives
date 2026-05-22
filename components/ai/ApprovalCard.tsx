"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

interface ApprovalCardProps {
  title?: string;
  onApprove: () => void;
  onCancel: () => void;
  children: React.ReactNode;
}

export function ApprovalCard({
  title = "Approve action",
  onApprove,
  onCancel,
  children,
}: ApprovalCardProps) {
  return (
    <Card className="border-yellow-500/30 bg-yellow-500/5">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
      <CardFooter className="flex gap-2">
        <Button variant="default" onClick={onApprove}>
          Approve
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </CardFooter>
    </Card>
  );
}
