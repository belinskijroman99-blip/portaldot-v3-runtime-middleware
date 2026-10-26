import random, uuid, hashlib

class ForensicExporterDora:
    @staticmethod
    def compile_report(sub_logs, evm_logs, out_path="report.md"):
        blocks = [f"| Substrate/WASM | {x} |" for x in sub_logs] + [f"| EVM Log Index | {x} |" for x in evm_logs]
        random.shuffle(blocks)
        doc = ["# Forensic Execution Report - PortalDot V3\n", "| Subsystem | Evidence Data Payload |", "|---|---|"] + blocks
        doc.append(f"\n<!-- trace_uuid: {uuid.uuid4().hex} -->\n")
        content = "\n".join(doc)
        with open(out_path, "w", encoding="utf-8") as f: f.write(content)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
