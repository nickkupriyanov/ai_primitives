"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, FolderGit2, GitCompare, MessagesSquare, Loader2 } from "lucide-react";

interface ScenarioDef {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  questions: string[];
}

const SCENARIOS: ScenarioDef[] = [
  {
    id: "conspectus",
    title: "Спроси по конспектам",
    description: "3 конспекта по Python: синтаксис, ООП, async. Задайте вопросы по материалу.",
    icon: <BookOpen className="h-5 w-5" />,
    questions: [
      "Как работает GIL в Python?",
      "Что такое dunder-методы?",
      "Зачем нужен event loop в asyncio?",
    ],
  },
  {
    id: "project-docs",
    title: "Спроси по документации проекта",
    description: "ROADMAP.md и описание архитектуры AI Primitives. Узнайте как устроен проект.",
    icon: <FolderGit2 className="h-5 w-5" />,
    questions: [
      "Какие модули уже реализованы?",
      "Как устроена архитектура бэкенда?",
    ],
  },
  {
    id: "compare",
    title: "Сравни 3 документа и найди противоречия",
    description: "Три документа о Python с намеренными расхождениями. Найдите, где они противоречат друг другу.",
    icon: <GitCompare className="h-5 w-5" />,
    questions: [
      "Какие противоречия между документами?",
    ],
  },
  {
    id: "faq",
    title: "Собери FAQ из набора заметок",
    description: "Заметки с вопросами-ответами по FastAPI и Next.js. Сгенерируйте сводный FAQ.",
    icon: <MessagesSquare className="h-5 w-5" />,
    questions: [
      "Сравни FastAPI и Next.js по маршрутизации и валидации",
      "Что такое FastAPI?",
    ],
  },
];

interface DemoScenariosProps {
  onLoad: (scenarioId: string) => void;
  onQuestionClick: (question: string) => void;
  loadedScenario: string | null;
  loading: boolean;
}

export function DemoScenarios({
  onLoad,
  onQuestionClick,
  loadedScenario,
  loading,
}: DemoScenariosProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {SCENARIOS.map((s) => {
        const isLoaded = loadedScenario === s.id;
        const isLoading = loading && loadedScenario === s.id;

        return (
          <Card key={s.id} className={isLoaded ? "border-blue-500/50" : ""}>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                {s.icon}
                <CardTitle className="text-base">{s.title}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">{s.description}</p>
              {!isLoaded ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onLoad(s.id)}
                  disabled={loading}
                >
                  {isLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  {isLoading ? "Loading..." : "Load Scenario"}
                </Button>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground uppercase">
                    Questions
                  </p>
                  {s.questions.map((q) => (
                    <Button
                      key={q}
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-left text-sm h-auto py-2"
                      onClick={() => onQuestionClick(q)}
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
