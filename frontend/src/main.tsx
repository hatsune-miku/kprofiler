import ReactDOM from "react-dom/client"
import App from "./components/App.tsx"
import "@/styles/index.scss"
import { NextUIProvider } from "@nextui-org/react"
import useDarkMode from "use-dark-mode"

const root = document.getElementById("root")!
window.global = globalThis

export function Main() {
  const darkMode = useDarkMode(false)
  const className = `${
    darkMode.value ? "dark" : ""
  } text-foreground bg-background main min-h-[100%]`

  return (
    <NextUIProvider className={className}>
      <main className={className}>
        <App />
      </main>
    </NextUIProvider>
  )
}

ReactDOM.createRoot(root).render(<Main />)
