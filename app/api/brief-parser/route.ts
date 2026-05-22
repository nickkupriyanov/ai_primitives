import { NextRequest, NextResponse } from "next/server";
import { openai } from "@/lib/ai/client";
import { AI_CONFIG } from "@/lib/ai/config";
import { briefParserPrompt } from "@/lib/ai/prompts";

export async function POST(req: NextRequest) {
  try {
    const { briefText } = await req.json();

    if (!briefText || typeof briefText !== "string") {
      return NextResponse.json(
        { error: "briefText is required" },
        { status: 400 }
      );
    }

    const response = await openai.chat.completions.create({
      model: AI_CONFIG.model,
      messages: [
        { role: "system", content: briefParserPrompt },
        { role: "user", content: briefText },
      ],
      response_format: { type: "json_object" },
      stream: true,
    });

    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        try {
          for await (const part of response) {
            const content = part.choices[0]?.delta?.content;
            if (content) {
              controller.enqueue(encoder.encode(content));
            }
          }
          controller.close();
        } catch (error) {
          controller.error(error);
        }
      },
    });

    return new Response(stream, {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to parse brief: ${message}` },
      { status: 500 }
    );
  }
}
