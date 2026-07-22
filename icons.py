import base64

_SVG_DICT = {
    "dashboard": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='7' height='9'></rect><rect x='14' y='3' width='7' height='5'></rect><rect x='14' y='12' width='7' height='9'></rect><rect x='3' y='16' width='7' height='5'></rect></svg>",
    "calendar": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='4' width='18' height='18' rx='2' ry='2'></rect><line x1='16' y1='2' x2='16' y2='6'></line><line x1='8' y1='2' x2='8' y2='6'></line><line x1='3' y1='10' x2='21' y2='10'></line></svg>",
    "settings": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='3'></circle><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'></path></svg>",
    "signout": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'></path><polyline points='16 17 21 12 16 7'></polyline><line x1='21' y1='12' x2='9' y2='12'></line></svg>",
    "patients": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'></path><circle cx='9' cy='7' r='4'></circle><path d='M23 21v-2a4 4 0 0 0-3-3.87'></path><path d='M16 3.13a4 4 0 0 1 0 7.75'></path></svg>",
    "doctors": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'></path><circle cx='12' cy='7' r='4'></circle><line x1='12' y1='11' x2='12' y2='14'></line><line x1='10' y1='12.5' x2='14' y2='12.5'></line></svg>",
    "analytics": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><line x1='18' y1='20' x2='18' y2='10'></line><line x1='12' y1='20' x2='12' y2='4'></line><line x1='6' y1='20' x2='6' y2='14'></line></svg>",
    "records": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'></path><polyline points='14 2 14 8 20 8'></polyline><line x1='16' y1='13' x2='8' y2='13'></line><line x1='16' y1='17' x2='8' y2='17'></line><polyline points='10 9 9 9 8 9'></polyline></svg>",
    "specialties": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polygon points='12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'></polygon></svg>",
    "availability": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><polyline points='12 6 12 12 16 14'></polyline></svg>",
    "blood": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z'></path></svg>",
    "gender": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='4'></circle><line x1='12' y1='16' x2='12' y2='22'></line><line x1='9' y1='19' x2='15' y2='19'></line></svg>",
    "health": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M22 12h-4l-3 9L9 3l-3 9H2'></path></svg>",
    "ai": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='11' width='18' height='10' rx='2'></rect><circle cx='12' cy='5' r='2'></circle><path d='M12 7v4'></path><line x1='8' y1='16' x2='8' y2='16'></line><line x1='16' y1='16' x2='16' y2='16'></line></svg>",
    "email": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z'></path><polyline points='22,6 12,13 2,6'></polyline></svg>",
    "add_doctor": "<svg viewBox='0 0 24 24' fill='none' stroke='#0f3e17' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'></path><circle cx='8.5' cy='7' r='4'></circle><line x1='20' y1='8' x2='20' y2='14'></line><line x1='23' y1='11' x2='17' y2='11'></line></svg>"
}

def get_svg_icon(name, size=24, color='#0f3e17', margin_right=8):
    if name not in _SVG_DICT:
        return ""
    svg_str = _SVG_DICT[name]
    
    # Inject xmlns if not present (required for data URI rendering in browsers)
    if 'xmlns=' not in svg_str:
        svg_str = svg_str.replace("<svg ", "<svg xmlns='http://www.w3.org/2000/svg' ", 1)
        
    # Replace default color if needed
    if color != '#0f3e17':
        svg_str = svg_str.replace("stroke='#0f3e17'", f"stroke='{color}'")
    
    # Base64 encode the SVG string
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
    margin = f"margin-right:{margin_right}px;" if margin_right > 0 else ""
    return f"<img src='data:image/svg+xml;base64,{b64}' style='width:{size}px; height:{size}px; display:inline-block; vertical-align:middle; {margin}'>"
