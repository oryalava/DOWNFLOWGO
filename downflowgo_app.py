import streamlit as st
import subprocess
import tempfile
from pathlib import Path
import time
import configparser


st.title("DOWNFLOWGO")

st.write("Web interface for DOWNFLOWGO that provides the most likely lava flow paths, including the area of coverage,"
         "and the runout distances of a lava flow along the line of steepest descent for given effusion rates"
         "Please see more details here: https://github.com/oryalava/DOWNFLOWGO/blob/main/README.md ")


# Select configuration file
config_file = st.file_uploader(
    "Select DOWNFLOWGO configuration file",
    type=["ini"]
)


# Run DOWNFLOWGO
if st.button("▶ Run DOWNFLOWGO"):

    if config_file is None:
        st.warning("Please select a .ini configuration file first.")
    else:
        # Create temporary configuration file
        with tempfile.NamedTemporaryFile(
            suffix=".ini",
            delete=False
        ) as tmp:
            tmp.write(config_file.getbuffer())
            config_path = Path(tmp.name)

        config = configparser.ConfigParser()
        config.read(config_path)

        name_vent = config["downflow"]["name_vent"]
        eruptions_folder = config["paths"]["eruptions_folder"]

        output_folder = Path(eruptions_folder) / name_vent

        status = st.empty()
        status.info("🔵 DOWNFLOWGO is running, please wait ...")

        # Start DOWNFLOWGO
        process = subprocess.Popen(
            [
                "python",
                "-u",
                "main_downflowgo.py",
                str(config_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Area where the output will be displayed
        output_area = st.empty()

        last_lines = []

        # Read output while DOWNFLOWGO is running
        for line in iter(process.stdout.readline, ""):

            line = line.rstrip()

            if line:
                last_lines.append(line)

                # Keep only the last 10 lines
                last_lines = last_lines[-10:]

                output_area.code(
                    "\n".join(last_lines)
                )

        # Wait for process to finish
        process.wait()

        # Final status
        if process.returncode == 0:

            st.success("🟢 Congratulations DOWNFLOWGO finished successfully 🌋🌋🌋")


        else:

            st.error(
                f"🔴DOWNFLOWGO failed (return code "
                f"{process.returncode})."
            )

        st.subheader("Results")

        map_file = output_folder / f"map_{name_vent}.png"

        if map_file.exists():
            st.image(
                str(map_file),
                caption="DOWNFLOWGO map",
                use_container_width=True
            )
        else:
            st.warning("Map not found.")