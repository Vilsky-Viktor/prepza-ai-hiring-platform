import net from "node:net"

// The site and the Auth emulator are at localhost addresses in the browser (as the frontend's
// settings say), but in the test container they're other containers. Chromium maps them with
// --host-resolver-rules; Firefox and WebKit have no such switch, so this forwards each local
// port to its container for every browser. FORWARDS (signed-in.sh): "8090=gateway:80,...".
export default async function forward() {
  const servers = (process.env.FORWARDS ?? "")
    .split(",")
    .filter(Boolean)
    .map((rule) => {
      const [port, target] = rule.split("=")
      const [host, targetPort] = target.split(":")
      const server = net.createServer((client) => {
        const upstream = net.connect(Number(targetPort), host)
        client.pipe(upstream).pipe(client)
        client.on("error", () => upstream.destroy())
        upstream.on("error", () => client.destroy())
      })

      // Both 127.0.0.1 and ::1: browsers try either for "localhost".
      return new Promise<net.Server>((resolve) =>
        server.listen({ port: Number(port), host: "::" }, () => resolve(server))
      )
    })
  const listening = await Promise.all(servers)

  return () => listening.forEach((server) => server.close())
}
