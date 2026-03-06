"use client"
import ChatMessage from "./ChatMessage"
import { Message } from "@/lib/types"
import { useEffect, useRef } from "react"

export default function MessageList({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
    <div ref={bottomRef} />
    </div>
  )
}