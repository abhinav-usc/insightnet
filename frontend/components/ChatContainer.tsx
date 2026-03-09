"use client"

import { useState, useRef, useCallback } from "react"
import MessageList from "./MessageList"
import ChatInput from "./ChatInput"
import { Message } from "@/lib/types"
import { queryStream } from "@/lib/api"
import Image from "next/image"

const SUGGESTED_QUERIES = [
  "Find epidemic modeling tools for COVID-19",
  "Compare agent-based vs compartmental models",
  "What tools support real-time surveillance data?",
]

export default function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    }

    const assistantId = crypto.randomUUID()
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      await queryStream(
        text,
        (chunk) => {
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: m.content + chunk }
                : m
            )
          )
        },
        controller.signal
      )
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, content: m.content || "Sorry, something went wrong. Please try again." }
            : m
        )
      )
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [])

  const clearChat = useCallback(() => {
    if (isStreaming) stopStreaming()
    setMessages([])
  }, [isStreaming, stopStreaming])

  const isEmpty = messages.length === 0

  return (
    <div className="w-[min(700px,95vw)] h-[min(600px,85vh)] flex flex-col rounded-2xl shadow-xl bg-white/50 backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/30">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="Logo" width={32} height={32} />
          <h2 className="text-xl font-bold text-[#1b183c]">Insight Net</h2>
        </div>
        {!isEmpty && (
          <button
            onClick={clearChat}
            className="text-xs text-[#314158]/60 hover:text-[#314158] transition px-2 py-1 rounded-md hover:bg-white/40"
          >
            Clear chat
          </button>
        )}
      </div>

      {/* Messages or Welcome */}
      {isEmpty ? (
        <div className="flex-1 flex flex-col items-center justify-center px-6 gap-6">
          <div className="text-center">
            <Image src="/logo.png" alt="Logo" width={48} height={48} className="mx-auto mb-3 opacity-80" />
            <p className="text-lg font-semibold text-[#1b183c]">What can I help you find?</p>
            <p className="text-sm text-[#314158]/60 mt-1">
              Search epidemic modeling tools, compare frameworks, or explore code
            </p>
          </div>
          <div className="flex flex-col gap-2 w-full max-w-md">
            {SUGGESTED_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                className="text-left text-sm text-[#314158] bg-white/60 hover:bg-white/80 rounded-lg px-4 py-2.5 shadow-sm transition border border-white/40"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <MessageList messages={messages} isStreaming={isStreaming} />
      )}

      <ChatInput
        onSend={sendMessage}
        disabled={isStreaming}
        onStop={stopStreaming}
        isStreaming={isStreaming}
      />
    </div>
  )
}
