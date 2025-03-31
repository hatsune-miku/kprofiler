import { useEffect, useState } from "react"

export interface Props extends React.HTMLAttributes<HTMLDivElement> {
  interval?: number
}

export default function SSProgress(props: Props) {
  const interval = props.interval ?? 250
  const [symbol, setSymbol] = useState(randomEmoji())

  useEffect(() => {
    const handle = setInterval(() => {
      setSymbol(randomEmoji())
    }, interval)
    return () => clearInterval(handle)
  }, [interval])

  return <div {...props}>{symbol}</div>
}

function randomEmoji(): string {
  const emojis = [
    "😊",
    "😍",
    "😎",
    "🍎",
    "🍌",
    "🍇",
    "🍓",
    "🍒",
    "🍉",
    "🍑",
    "🍍",
    "🥥",
    "🍔",
    "🍕",
    "🍩",
    "👻",
    "🎂",
    "🎈",
    "🎉",
    "🎁",
  ]

  const randomIndex = Math.floor(Math.random() * emojis.length)
  return emojis[randomIndex]
}
