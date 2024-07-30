/**
 * v0 by Vercel.
 * @see https://v0.dev/t/5CKyYeywbK5
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
import { Button } from "@/components/ui/button"

export default function Component() {
  return (
    <div className="mx-auto max-w-md space-y-6 px-4 py-12 sm:px-6 lg:px-8">
      <div className="space-y-4 text-center">
        <h2 className="text-2xl font-bold tracking-tight">Connect Socials</h2>
        <p className="text-muted-foreground">Connect your social accounts to get started.</p>
      </div>
      <div className="space-y-2">
        <Button variant="outline" className="w-full">
          Connect Twitter
        </Button>
        <Button variant="outline" className="w-full">
          Connect LinkedIn
        </Button>
      </div>
      <div className="text-center text-sm text-muted-foreground">Do this later</div>
    </div>
  )
}