/**
 * v0 by Vercel.
 * @see https://v0.dev/t/O7gLJ35uK6O
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectGroup, SelectItem } from "@/components/ui/select"

export default function Component() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="flex items-center h-16 px-6 border-b shrink-0">
        <Link href="#" className="flex items-center gap-2 text-lg font-semibold" prefetch={false}>
          <RecycleIcon className="w-6 h-6" />
          <span>PostOnce</span>
        </Link>
        <nav className="ml-auto flex items-center gap-4">
          <Link href="#" className="text-muted-foreground hover:text-foreground" prefetch={false}>
            Accounts
          </Link>
          <Link href="#" className="text-muted-foreground hover:text-foreground" prefetch={false}>
            Settings
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Feedback
          </Button>
          <div className="flex items-center gap-2">
            <Avatar className="w-8 h-8 border">
              <AvatarImage src="/placeholder-user.jpg" />
              <AvatarFallback>AC</AvatarFallback>
            </Avatar>
            <div className="grid gap-0.5 text-xs">
              <div className="font-medium">John Doe</div>
              <div className="text-muted-foreground">Newsletter</div>
            </div>
          </div>
        </nav>
      </header>
      <main className="flex-1 flex justify-center items-start gap-6 p-6">
        <div className="w-full max-w-md">
          <Card className="flex flex-col gap-4">
            <CardHeader>
              <CardTitle>Connected Accounts</CardTitle>
              <CardDescription>Quickly access your content repurposing tools.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <Link
                href="#"
                className="relative flex flex-col items-center gap-2 p-4 rounded-lg bg-muted hover:bg-muted/50 transition-colors border-2 border-primary"
                prefetch={false}
              >
                <TwitterIcon className="w-8 h-8" />
                <span className="text-sm font-medium">Twitter</span>
                <div className="absolute bottom-2 right-2 flex items-center justify-center bg-primary text-primary-foreground rounded-full w-5 h-5">
                  <CheckIcon className="h-3 w-3" />
                </div>
              </Link>
              <Link
                href="#"
                className="relative flex flex-col items-center gap-2 p-4 rounded-lg bg-muted hover:bg-muted/50 transition-colors border-2 border-primary"
                prefetch={false}
              >
                <InstagramIcon className="w-8 h-8" />
                <span className="text-sm font-medium">Instagram</span>
                <div className="absolute bottom-2 right-2 flex items-center justify-center bg-primary text-primary-foreground rounded-full w-5 h-5">
                  <CheckIcon className="h-3 w-3" />
                </div>
              </Link>
              <Link
                href="#"
                className="relative flex flex-col items-center gap-2 p-4 rounded-lg bg-muted hover:bg-muted/50 transition-colors border-2 border-primary"
                prefetch={false}
              >
                <LinkedinIcon className="w-8 h-8" />
                <span className="text-sm font-medium">LinkedIn</span>
                <div className="absolute bottom-2 right-2 flex items-center justify-center bg-primary text-primary-foreground rounded-full w-5 h-5">
                  <CheckIcon className="h-3 w-3" />
                </div>
              </Link>
              <Link
                href="#"
                className="relative flex flex-col items-center gap-2 p-4 rounded-lg bg-muted hover:bg-muted/50 transition-colors"
                prefetch={false}
              >
                <FacebookIcon className="w-8 h-8" />
                <span className="text-sm font-medium">Facebook</span>
                <div className="absolute bottom-2 right-2 flex items-center justify-center bg-primary text-primary-foreground rounded-full w-5 h-5">
                  <PlusIcon className="h-3 w-3" />
                </div>
              </Link>
              <a
                href="#"
                className="relative flex flex-col items-center gap-2 p-4 rounded-lg bg-muted hover:bg-muted/50 transition-colors"
              >
                <PlusIcon className="w-8 h-8" />
                <span className="text-sm font-medium">Request Platform</span>
              </a>
            </CardContent>
          </Card>
        </div>
        <div className="w-full max-w-md">
          <Card className="flex flex-col gap-4">
            <CardHeader>
              <CardTitle>Content Hub</CardTitle>
              <CardDescription>Easily access the main features of the tool.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="beehiiv-url">Beehiiv Article URL</Label>
                <Input id="beehiiv-url" placeholder="Enter your Beehiiv article URL" />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="content-type">Content Type</Label>
                <Select id="content-type" className="w-full">
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select content type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value="pre-newsletter-cta">
                        <div className="flex items-center gap-2">
                          <TwitterIcon className="w-5 h-5" />
                          <span>Pre-Newsletter CTA</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="post-newsletter-cta">
                        <div className="flex items-center gap-2">
                          <TwitterIcon className="w-5 h-5" />
                          <span>Post-Newsletter CTA</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="twitter-thread">
                        <div className="flex items-center gap-2">
                          <TwitterIcon className="w-5 h-5" />
                          <span>Thread</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="twitter-long-form">
                        <div className="flex items-center gap-2">
                          <TwitterIcon className="w-5 h-5" />
                          <span>Long-form Post</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="linkedin-long-form">
                        <div className="flex items-center gap-2">
                          <LinkedinIcon className="w-5 h-5" />
                          <span>Long-form Post</span>
                        </div>
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>
              <Link
                href="#"
                className="flex flex-col items-center gap-2 p-4 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                prefetch={false}
              >
                <BookIcon className="w-8 h-8" />
                <span className="text-sm font-medium">Generate</span>
              </Link>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

function BookIcon(props) {
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
      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
    </svg>
  )
}


function CheckIcon(props) {
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
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}


function FacebookIcon(props) {
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
      <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
    </svg>
  )
}


function InstagramIcon(props) {
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
      <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
      <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
    </svg>
  )
}


function LinkedinIcon(props) {
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
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect width="4" height="12" x="2" y="9" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  )
}


function PlusIcon(props) {
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
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  )
}


function RecycleIcon(props) {
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
      <path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5" />
      <path d="M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12" />
      <path d="m14 16-3 3 3 3" />
      <path d="M8.293 13.596 7.196 9.5 3.1 10.598" />
      <path d="m9.344 5.811 1.093-1.892A1.83 1.83 0 0 1 11.985 3a1.784 1.784 0 0 1 1.546.888l3.943 6.843" />
      <path d="m13.378 9.633 4.096 1.098 1.097-4.096" />
    </svg>
  )
}


function TwitterIcon(props) {
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
      <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
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