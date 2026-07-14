import streamlit as st
html = """
<table border="1">
<tr><td>Test SVG</td><td><svg viewBox='0 0 24 24' width='24' height='24' stroke='red' stroke-width='2' fill='none'><circle cx='12' cy='12' r='10'></circle></svg></td></tr>
</table>
"""
st.markdown(html, unsafe_allow_html=True)
