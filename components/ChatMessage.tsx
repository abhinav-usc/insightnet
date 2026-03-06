import { Message } from "@/lib/types"

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`px-4 py-2 rounded-xl max-w-[70%] text-md shadow-sm ${
          isUser
            ? "bg-white text-[#314158] rounded-tr-none"
            : "bg-[#B1CBF5]/60 text-[#314158] rounded-tl-none"
        }`}
      >
        <p>{message.content}</p>
      </div>
    </div>
  )
}