import { connect } from "node:net"

// Redis on the stack's network (compose/infrastructure.yml), reached from the test process.
const REDIS_HOST = "redis"
const REDIS_PORT = 6379

/** Runs one Redis command and gives its reply's first line; no client library, as the tests need
 * only a counter set now and then. */
export function redis(...args: string[]): Promise<string> {
  const command = `*${args.length}\r\n${args.map((arg) => `$${Buffer.byteLength(arg)}\r\n${arg}\r\n`).join("")}`

  return new Promise((done, failed) => {
    const socket = connect(REDIS_PORT, REDIS_HOST, () => socket.write(command))
    socket.once("data", (reply) => {
      socket.end()
      const line = reply.toString().split("\r\n")[0]

      if (line.startsWith("-")) {
        failed(new Error(line))

        return
      }

      done(line)
    })
    socket.once("error", failed)
  })
}
