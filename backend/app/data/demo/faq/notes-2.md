# Next.js FAQ Notes

## Q: What is Next.js App Router?

The App Router is Next.js's modern routing system based on the file system. Pages are `page.tsx`, layouts are `layout.tsx`, and API routes are `route.ts`.

## Q: What are Server Components?

Server Components run on the server and never ship client-side JavaScript. They can directly access databases and filesystems. They are the default in App Router.

## Q: What are Server Actions?

Server Actions are async functions marked with `"use server"` that run on the server. They can be called from Client Components and handle form submissions, data mutations, and API calls without creating a separate API route.

## Q: How do you handle loading states?

Next.js provides `loading.tsx` files for route-level loading UI, and React's `useTransition` hook for pending states during server action calls.

## Q: What is static vs dynamic rendering?

By default, Next.js tries to statically render pages at build time. When you use dynamic functions like `cookies()`, `headers()`, or `searchParams`, the page becomes dynamically rendered at request time.
