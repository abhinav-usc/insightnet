"use client"

import { useState } from "react"
import MessageList from "./MessageList"
import ChatInput from "./ChatInput"
import { Message } from "@/lib/types"
import Image from "next/image";

export default function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([])

  const sendMessage = (text: string) => {
    const newMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text
    }

    const sampleReplyMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "Hello! This is a sample reply. You can replace this with actual API calls to get dynamic responses."
    }

    setMessages(prev => [...prev, newMessage, sampleReplyMessage])
  }

  return (
    <div className="w-[700px] h-[600px] flex flex-col rounded-xl shadow-lg bg-white/50 p-1">
      <div className="header flex items-center gap-1 p-4">
        <Image src="/logo.png" alt="Logo" width={35} height={35} />
        <h2 className="text-2xl font-bold p-2 text-[#1b183c]">Insight Net</h2>
      </div>
      <MessageList messages={messages} />
      <ChatInput onSend={sendMessage} />
    </div>
  )
}