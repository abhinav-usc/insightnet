"use client"

import { useState, useRef, useEffect } from "react"

type ChatInputProps = {
  onSend: (text: string) => void
  disabled?: boolean
  isStreaming?: boolean
  onStop?: () => void
}

export default function ChatInput({ onSend, disabled, isStreaming, onStop }: ChatInputProps) {
  const [text, setText] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea to fit content
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "0"
    el.style.height = Math.min(el.scrollHeight, 120) + "px"
  }, [text])

  // Re-focus input after streaming ends
  useEffect(() => {
    if (!isStreaming) textareaRef.current?.focus()
  }, [isStreaming])

  const handleSend = () => {
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText("")
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="px-4 pb-4 pt-2">
      <div className="flex items-end gap-2 bg-white rounded-xl shadow-sm px-3 py-2 border border-white/40">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          className="flex-1 text-sm outline-none text-black bg-transparent resize-none py-1.5 placeholder:text-[#314158]/40"
          placeholder={isStreaming ? "Waiting for response..." : "Ask about epidemic modeling tools..."}
          disabled={disabled}
        />
        {isStreaming ? (
          <button
            onClick={onStop}
            className="shrink-0 w-8 h-8 flex items-center justify-center bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
            title="Stop"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
              <rect width="12" height="12" rx="1" />
            </svg>
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            className="shrink-0 w-8 h-8 flex items-center justify-center bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-30"
            title="Send"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        )}
      </div>
      <p className="text-[10px] text-[#314158]/40 text-center mt-1.5">
        Shift+Enter for new line
      </p>
    </div>
  )
}
