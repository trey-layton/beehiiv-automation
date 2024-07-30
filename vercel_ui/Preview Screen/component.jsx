/**
 * v0 by Vercel.
 * @see https://v0.dev/t/6IuymMEC958
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel } from "@/components/ui/alert"

export default function Component() {
  const [isPosting, setIsPosting] = useState(false)
  const [postStatus, setPostStatus] = useState(null)
  const handlePost = async () => {
    setIsPosting(true)
    try {
      const response = await fetch("YOUR_API_URL", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: "This is a sample tweet" }),
      })
      if (response.ok) {
        setPostStatus("success")
      } else {
        setPostStatus("error")
      }
    } catch (error) {
      setPostStatus("error")
    } finally {
      setIsPosting(false)
    }
  }
  return (
    <div className="flex flex-col h-screen">
      <header className="bg-black text-white px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Previewing Twitter Thread</h1>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="text-white">
            <FilePenIcon className="w-5 h-5" />
            <span className="sr-only">Edit</span>
          </Button>
          <Button variant="ghost" size="icon" className="text-white">
            <XIcon className="w-5 h-5" />
            <span className="sr-only">Close</span>
          </Button>
        </div>
      </header>
      <div className="flex-1 overflow-auto">
        <div className="max-w-2xl mx-auto py-8 px-4">
          <div className="space-y-8">
            <div className="flex items-start gap-4">
              <Avatar className="shrink-0 border-2 border-primary">
                <AvatarImage src="/placeholder-user.jpg" />
                <AvatarFallback>CN</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="font-bold text-black">Shadcn</div>
                  <div className="text-gray-500 text-sm">@shadcn</div>
                  <div className="text-gray-500 text-sm">· 2h</div>
                </div>
                <div className="text-black">
                  <p className="animate-typing">
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nisl nec ultricies lacinia,
                    nisl nisl aliquam nisl, eget aliquam nisl nisl sit amet nisl. Sed euismod, nisl nec ultricies
                    lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl sit amet nisl.
                  </p>
                </div>
                <div className="flex items-center gap-4 mt-2">
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <MessageCircleIcon className="w-5 h-5" />
                    <span className="sr-only">Reply</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <RepeatIcon className="w-5 h-5" />
                    <span className="sr-only">Retweet</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <HeartIcon className="w-5 h-5" />
                    <span className="sr-only">Like</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <ShareIcon className="w-5 h-5" />
                    <span className="sr-only">Share</span>
                  </Button>
                </div>
              </div>
            </div>
            <Separator />
            <div className="flex items-start gap-4">
              <Avatar className="shrink-0 border-2 border-primary">
                <AvatarImage src="/placeholder-user.jpg" />
                <AvatarFallback>CN</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="font-bold text-black">Shadcn</div>
                  <div className="text-gray-500 text-sm">@shadcn</div>
                  <div className="text-gray-500 text-sm">· 2h</div>
                </div>
                <div className="text-black">
                  <p className="animate-typing">
                    Sed euismod, nisl nec ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl sit amet
                    nisl. Sed euismod, nisl nec ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl sit
                    amet nisl.
                  </p>
                </div>
                <div className="flex items-center gap-4 mt-2">
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <MessageCircleIcon className="w-5 h-5" />
                    <span className="sr-only">Reply</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <RepeatIcon className="w-5 h-5" />
                    <span className="sr-only">Retweet</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <HeartIcon className="w-5 h-5" />
                    <span className="sr-only">Like</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <ShareIcon className="w-5 h-5" />
                    <span className="sr-only">Share</span>
                  </Button>
                </div>
              </div>
            </div>
            <Separator />
            <div className="flex items-start gap-4">
              <Avatar className="shrink-0 border-2 border-primary">
                <AvatarImage src="/placeholder-user.jpg" />
                <AvatarFallback>CN</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="font-bold text-black">Shadcn</div>
                  <div className="text-gray-500 text-sm">@shadcn</div>
                  <div className="text-gray-500 text-sm">· 2h</div>
                </div>
                <div className="text-black">
                  <p className="animate-typing">
                    Sed euismod, nisl nec ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl sit amet
                    nisl. Sed euismod, nisl nec ultricies lacinia, nisl nisl aliquam nisl, eget aliquam nisl nisl sit
                    amet nisl.
                  </p>
                </div>
                <div className="flex items-center gap-4 mt-2">
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <MessageCircleIcon className="w-5 h-5" />
                    <span className="sr-only">Reply</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <RepeatIcon className="w-5 h-5" />
                    <span className="sr-only">Retweet</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <HeartIcon className="w-5 h-5" />
                    <span className="sr-only">Like</span>
                  </Button>
                  <Button variant="ghost" size="icon" className="text-gray-500 hover:text-primary">
                    <ShareIcon className="w-5 h-5" />
                    <span className="sr-only">Share</span>
                  </Button>
                </div>
              </div>
            </div>
            <div className="flex justify-center gap-4">
              <Button onClick={handlePost} disabled={isPosting}>
                {isPosting ? "Posting..." : "Post"}
              </Button>
              <Button variant="secondary">Regenerate</Button>
              <Button variant="secondary">Cancel</Button>
            </div>
          </div>
        </div>
      </div>
      {postStatus === "success" && (
        <AlertDialog>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Success!</AlertDialogTitle>
              <AlertDialogDescription>Your tweet has been posted successfully.</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Close</AlertDialogCancel>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
      {postStatus === "error" && (
        <AlertDialog>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Failed to post</AlertDialogTitle>
              <AlertDialogDescription>
                There was an error posting your tweet. Please try again later.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Close</AlertDialogCancel>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  )
}

function FilePenIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 22h6a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v10" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
      <path d="M10.4 12.6a2 2 0 1 1 3 3L8 21l-4 1 1-4Z" />
    </svg>
  )
}


function HeartIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
    </svg>
  )
}


function MessageCircleIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
    </svg>
  )
}


function RepeatIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m17 2 4 4-4 4" />
      <path d="M3 11v-1a4 4 0 0 1 4-4h14" />
      <path d="m7 22-4-4 4-4" />
      <path d="M21 13v1a4 4 0 0 1-4 4H3" />
    </svg>
  )
}


function ShareIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" x2="12" y1="2" y2="15" />
    </svg>
  )
}


function XIcon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  )
}