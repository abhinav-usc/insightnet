"use client"

import { useState } from "react"

export default function ChatInput({ onSend }: { onSend: (text: string) => void }) {
  const [text, setText] = useState("")

  const handleSend = () => {
    if (!text) return
    onSend(text)
    setText("")
  }

  return (
    <div className="flex p-4">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="flex-1 text-md outline-none bg-white rounded-lg px-4 py-3 shadow-sm"
          placeholder="Ask something..."
        />
        <button
          onClick={handleSend}
          className="ml-2 px-4 py-3 bg-blue-600 text-white text-md rounded-lg shadow-md hover:bg-blue-700 transition"
        >
          Send
        </button>
    </div>
  )
}