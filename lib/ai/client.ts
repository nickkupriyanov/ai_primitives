import OpenAI from "openai";

const apiKey = process.env.AI_API_KEY;
const baseURL = process.env.BASE_URL

if (!apiKey) {
  throw new Error(
    "Missing AI_API_KEY environment variable. Please set it in .env.local"
  );
}

export const openai = new OpenAI({
  apiKey,
  baseURL,
});
