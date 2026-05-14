from datetime import datetime, timezone
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ReportSaverInput(BaseModel):
    content: str = Field(description="Full text content to save as a report")
    filename: str = Field(
        default="",
        description="Filename without extension. Defaults to a timestamped name.",
    )
    output_dir: str = Field(
        default="",
        description="Directory to save the report. Defaults to current working directory.",
    )


class ReportSaverTool(BaseTool):
    name: str = "save_report"
    description: str = (
        "Save a text report to a local .txt file. "
        "Returns the absolute path of the saved file."
    )
    args_schema: type[BaseModel] = ReportSaverInput

    def _run(self, content: str, filename: str = "", output_dir: str = "") -> str:
        out_dir = Path(output_dir).resolve() if output_dir else Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"inbox_summary_{ts}"

        path = out_dir / f"{filename}.txt"
        path.write_text(content, encoding="utf-8")
        return f"Report saved to: {path}"
