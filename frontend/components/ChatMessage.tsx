"use client"

import { Message } from "@/lib/types"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

type ChatMessageProps = {
  message: Message
  isLastAssistant?: boolean
  isStreaming?: boolean
}

export default function ChatMessage({ message, isLastAssistant, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user"
  const showCursor = isLastAssistant && isStreaming && message.content.length > 0

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`px-4 py-2.5 rounded-xl text-sm shadow-sm ${
          isUser
            ? "bg-white text-[#314158] rounded-tr-none max-w-[70%]"
            : "bg-[#B1CBF5]/60 text-[#314158] rounded-tl-none max-w-[85%]"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : message.content ? (
          <div className="prose prose-sm max-w-none prose-headings:text-[#1b183c] prose-headings:mt-3 prose-headings:mb-1 prose-p:my-1.5 prose-a:text-blue-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:text-xs prose-pre:rounded-lg prose-table:text-xs prose-li:my-0.5 prose-strong:text-[#1b183c]">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {showCursor && <span className="inline-block w-0.5 h-4 bg-[#314158]/60 ml-0.5 animate-blink align-text-bottom" />}
          </div>
        ) : (
          <div className="flex items-center gap-1.5 py-1">
            <span className="w-1.5 h-1.5 bg-[#314158]/40 rounded-full animate-bounce [animation-delay:0ms]" />
            <span className="w-1.5 h-1.5 bg-[#314158]/40 rounded-full animate-bounce [animation-delay:150ms]" />
            <span className="w-1.5 h-1.5 bg-[#314158]/40 rounded-full animate-bounce [animation-delay:300ms]" />
          </div>
        )}
      </div>
    </div>
  )
}
