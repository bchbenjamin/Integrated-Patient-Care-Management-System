import os, glob, re

for file in glob.glob("views/*.py"):
    with open(file, "r") as f:
        content = f.read()
    
    # Replace single line SVG headers
    # e.g., st.markdown(f"<h2...>{get_svg_icon...} Title</h2>", unsafe_allow_html=True)
    pattern = r'st\.markdown\(\s*f"(<[^>]+>)\s*\{get_svg_icon\([^}]+\)\}(.*?)(<\/[^>]+>)"\s*,\s*unsafe_allow_html=True\s*\)'
    # Wait, getting the regex exactly right is hard. 
    # Let's just find any st.markdown containing get_svg_icon and change it to st.html
    # Only if it is exactly one line.
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'st.markdown(' in line and 'get_svg_icon(' in line and 'unsafe_allow_html=True' in line:
            # Change st.markdown to st.html and remove unsafe_allow_html=True
            line = line.replace('st.markdown(', 'st.html(')
            line = line.replace(', unsafe_allow_html=True', '')
            lines[i] = line
            
    with open(file, "w") as f:
        f.write('\n'.join(lines))
