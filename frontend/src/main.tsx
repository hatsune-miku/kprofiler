import ReactDOM from "react-dom/client"
import App from "./components/App.tsx"
import "@/styles/index.scss"
import { NextUIProvider } from "@nextui-org/react"
import useDarkMode from "use-dark-mode"

const root = document.getElementById("root")!
window.global = globalThis

function Main() {
  const darkMode = useDarkMode(false)

  return (
    <NextUIProvider>
      <main
        className={`${
          darkMode.value ? "dark" : ""
        } text-foreground bg-background main`}
      >
        <App />
      </main>
    </NextUIProvider>
  )
}

ReactDOM.createRoot(root).render(<Main />)
