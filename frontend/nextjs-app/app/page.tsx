"use client";

import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { useDentalChat } from "@/hooks/use-dental-chat";

import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ChatHeader } from "@/components/chat/chat-header";
import { ChatWelcome } from "@/components/chat/chat-welcome";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";
import { ChatLoading } from "@/components/chat/chat-loading";
import { AboutDialog } from "@/components/chat/about-dialog";

export default function ChatPage() {
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  const {
    input,
    setInput,
    sessions,
    activeSessionId,
    activeSession,
    currentMessages,
    isLoading,
    isCheckingAuth,
    isDark,
    openSources,
    setOpenSources,
    messagesEndRef,
    user,
    toggleTheme,
    handleNewChat,
    handleSelectSession,
    handleDeleteSession,
    handleClearAllChat,
    handleSubmit,
    handleLogout,
  } = useDentalChat();

  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex gap-1">
          <span className="h-3 w-3 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
          <span className="h-3 w-3 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
          <span className="h-3 w-3 animate-bounce rounded-full bg-primary" />
        </div>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        isDark={isDark}
        user={user}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onClearAllChat={handleClearAllChat}
        onToggleTheme={toggleTheme}
        onAboutOpen={() => setIsAboutOpen(true)}
        onLogout={handleLogout}
      />

      <SidebarInset className="flex flex-col h-screen">
        <ChatHeader
          title={activeSession ? activeSession.title : "Cuộc trò chuyện mới"}
          isDark={isDark}
          onToggleTheme={toggleTheme}
        />

        {/* Chat Area - Scrollable */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="mx-auto max-w-3xl px-4 py-6 md:px-8">
              {currentMessages.length === 0 ? (
                <ChatWelcome onSelectSuggestion={setInput} />
              ) : (
                <div className="flex flex-col gap-5">
                  {currentMessages.map((msg, index) => (
                    <ChatMessage
                      key={index}
                      message={msg}
                      index={index}
                      isSourceOpen={openSources[index] || false}
                      onSourceToggle={(open) =>
                        setOpenSources((prev) => ({
                          ...prev,
                          [index]: open,
                        }))
                      }
                    />
                  ))}


                  <div ref={messagesEndRef} className="h-4" />
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

        <ChatInput
          input={input}
          isLoading={isLoading}
          onInputChange={setInput}
          onSubmit={handleSubmit}
        />
      </SidebarInset>

      <AboutDialog open={isAboutOpen} onOpenChange={setIsAboutOpen} />
    </SidebarProvider>
  );
}
