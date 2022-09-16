import streamlit as st

def set_page_container_style(
        max_width: int = 1100, max_width_100_percent: bool = False,
        padding_top: int = 1, padding_right: int = 10, padding_left: int = 1, padding_bottom: int = 10,
        color: str = 'black', background_color: str = 'white',
    ):
        if max_width_100_percent:
            max_width_str = f'max-width: 100%;'
        else:
            max_width_str = f'max-width: {max_width}px;'
        st.markdown(
            f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {padding_top}rem;
                }}
                .reportview-container .main .block-container {{
                    {max_width_str}
                    padding-top: {padding_top}rem;
                    padding-right: {padding_right}rem;
                    padding-left: {padding_left}rem;
                    padding-bottom: {padding_bottom}rem;
                }}
                .reportview-container .main {{
                    color: {color};
                    background-color: {background_color};
                }}
            </style>
            ''',
            unsafe_allow_html=True,
        )


def plot_title():
    st.set_page_config(
        page_title="RAC Dynamic Clustering",
        page_icon=":car:"
    )

    padding_top = 0
    padding_bottom = 10
    padding_left = 1
    padding_right = 10
    # max_width_str = f'max-width: 100%;'
    st.markdown(f'''
                <style>
                    .reportview-container .sidebar-content {{
                        padding-top: {padding_top}rem;
                    }}
                    .reportview-container .main .block-container {{
                        padding-top: {padding_top}rem;
                        padding-right: {padding_right}rem;
                        padding-left: {padding_left}rem;
                        padding-bottom: {padding_bottom}rem;
                    }}
                </style>
                ''', unsafe_allow_html=True,
                )

    # Add rac logo
    st.markdown(
        """
        <div>
            <img class = 'raclogo' src="https://cdn.productreview.com.au/resize/listing-picture/2634fafd-94e5-3027-a63f-0b0794a22cc9?width=1200&amp;height=630&amp;v=2" alt="" width="200" height="105" />
        </div>
        """,
        unsafe_allow_html=True
    )

    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # st.image('./company logos/rac_logo.png', width=100)
    st.title('wanted this')
    st.markdown(
        """
        <div style = "position: relative; top:-25px">
            <font size="+2">powered by </font><img src="https://geoscape.com.au/wp-content/uploads/2020/02/partner-finity-350.png" alt="" width="42" height="15" />
        </div>
        """,
        unsafe_allow_html=True
    )
