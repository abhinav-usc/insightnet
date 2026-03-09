"use client"

import ChatMessage from "./ChatMessage"
import { Message } from "@/lib/types"
import { useEffect, useRef } from "react"

type MessageListProps = {
  messages: Message[]
  isStreaming?: boolean
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Find the last assistant message index
  const lastAssistantIdx = messages.reduce(
    (acc, m, i) => (m.role === "assistant" ? i : acc),
    -1
  )

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin">
      {messages.map((msg, i) => (
        <ChatMessage
          key={msg.id}
          message={msg}
          isLastAssistant={i === lastAssistantIdx}
          isStreaming={isStreaming}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
