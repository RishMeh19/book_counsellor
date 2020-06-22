
VERIFY_TOKEN = "1905199712041994RoRiRa$"
PAGE_ACCESS_TOKEN = 'EAAD5ZBn31OLMBAGlaZCZB3VO4X3KaibtmZCoc2Oi2plbkLP4yCIqmm9rwEzYcj8efNyQ0GfSCuiRx20BwM4P0h8MxwWxDJeZAPY91dbZArDetD2Rd0lN0VcV7iqkRr2evqPSrK1qGASUso4bMOx3ybK08Xui42w499rcT7whatWQZDZD'
age_mapping = {
    'below 8' : 1,
    '8-15' : 2,
    '15-40' : 3,
    '40-65' :4,
    'above 65' :5
}
q_dict = {
    0: ["Introductory postback",''],
    1: ["Type of book you preder",'typo'],
    2: ["Any specific genres in your mind. If you have no specific genres in your mind, type 'no'",''],
    3: ["Genre confirm postback",'genres'],
    4: ["Enter your age(eg, 13,8), if you do not want age filter to get applied, type 'no'", ''],
    5: ["Age confirm postback",'age'],
    6: ["Any particular author you prefer, type 'no' if you do not have any specific author choices",''],
    7: ["Author confirm postback",'author'],
    8: ["Are you happy with our suggestions postback",''],
    9:["One time notification postback, if requires" ,'']

}