const fs = require("fs")
const path = require("path")

const routesTypes = path.join(process.cwd(), ".next", "types", "routes.d.ts")

if (!fs.existsSync(routesTypes)) {
  fs.mkdirSync(path.dirname(routesTypes), { recursive: true })
  fs.writeFileSync(routesTypes, "export {}\n", "utf-8")
}
