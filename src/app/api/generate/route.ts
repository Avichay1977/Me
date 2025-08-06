import { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";

const MODEL_NAME = "gemini-1.5-pro-latest";

const SYSTEM_PROMPT = `You are a helpful and expert assistant for the music production software Cubase.

Your tasks are:
1.  If the user provides an image and asks a question about it, answer the question concisely.
2.  If the user provides a text prompt asking to create a script, translate the request into precise, executable JavaScript code that conforms to the Cubase Scripting API.
    - When generating a script, your output must ONLY contain the JavaScript code. Do not add any explanations or any other text outside the code block.
    - If you cannot fulfill a script request, return a short error message inside a JavaScript comment.

Example for a script request:
User: "Create a mono audio track named 'Vocals'"
Assistant:
// Creates a mono audio track named 'Vocals'
cubase.createAudioTrack('Vocals', 'mono');

Example for a visual question:
User: (Image of a Cubase mixer) "What does the red 'R' button do?"
Assistant: "The red 'R' button is the 'Read' button for automation. When it's enabled, the track will read and follow any existing automation data."`;

async function fileToGenerativePart(file: string, mimeType: string) {
  return {
    inlineData: {
      data: file,
      mimeType,
    },
  };
}

export async function POST(req: NextRequest) {
  try {
    const { prompt, image } = await req.json();

    if (!prompt) {
      return NextResponse.json({ error: "Prompt is required." }, { status: 400 });
    }

    const API_KEY = process.env.GOOGLE_API_KEY;
    if (!API_KEY) {
      return NextResponse.json({ error: "Google API key is not set." }, { status: 500 });
    }

    const genAI = new GoogleGenerativeAI(API_KEY);
    const model = genAI.getGenerativeModel({ model: MODEL_NAME });

    const generationConfig = {
      temperature: 0.4,
      topK: 1,
      topP: 1,
      maxOutputTokens: 2048,
    };

    const safetySettings = [
      { category: HarmCategory.HARM_CATEGORY_HARASSMENT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
      { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
      { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
      { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
    ];

    const parts = [
        { text: SYSTEM_PROMPT },
        { text: `User query: ${prompt}` },
    ];

    if (image) {
        const image_data_url = image.split(',')[1];
        const mime_type = image.match(/data:(.*);base64,/)[1];
        parts.push({
            inline_data: {
                mime_type: mime_type,
                data: image_data_url
            }
        });
    }

    const result = await model.generateContent({
        contents: [{ role: "user", parts }],
        generationConfig,
        safetySettings,
    });

    const text = result.response.text();

    // Simple check if the response is likely code
    const isCode = text.includes('cubase.') || text.trim().startsWith('//');

    return NextResponse.json({ text, isCode });

  } catch (error: any) {
    console.error("Error in generate API:", error);
    return NextResponse.json({ error: error.message || "An unexpected error occurred." }, { status: 500 });
  }
}
