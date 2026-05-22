import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, FormInput, Wrench } from "lucide-react";

const modules = [
  {
    title: "Brief Parser",
    description: "Paste a product description and get structured JSON output with persona, pain points, risks, and follow-up questions.",
    href: "/brief-parser",
    icon: FileText,
  },
  {
    title: "AI Form Assistant",
    description: "Let AI suggest values for a project form. Review, edit, and approve before applying any changes.",
    href: "/form-assistant",
    icon: FormInput,
  },
  {
    title: "Tool Calling Playground",
    description: "See how the model chooses tools, preview arguments, and approve execution before any side effects.",
    href: "/tool-playground",
    icon: Wrench,
  },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      <div className="mb-10 space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">AI Primitives Playground</h1>
        <p className="text-muted-foreground">
          Interactive examples of core AI patterns: streaming, structured output, schema validation, tool calling, and approval flows.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {modules.map((mod) => {
          const Icon = mod.icon;
          return (
            <Card key={mod.href} className="flex flex-col">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{mod.title}</CardTitle>
                </div>
                <CardDescription>{mod.description}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto">
                <Link href={mod.href}>
                  <Button className="w-full">Open</Button>
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
