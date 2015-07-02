<html>
<head>
    <style type="text/css">
        ${css}
        #id1 {
        text-align:right;
        border: 1px solid #ffffff;
        font-size:8;
        }
        #id2 {
        text-align:center;
        border: 1px solid #ffffff;
        font-size:8;
        }
        #id3 {
        border: 2.5px solid #000000;
        }
        #id4 {
        border: 1px solid #000000;
        font-size:10;
        }
        #id5 {
        border: 1px solid #ffffff;
        border-bottom-color:#000000;
        }
        #id6 {
        text-align:left;
        border: 1px solid #ffffff;
        font-size:8;
        }
        #id7 {
        text-align:center;
        border: 1px solid #000000;
        font-size:7;
        }
        #id8 {
        text-align:center;
        border: 1px solid #ffffff;
        font-size:10;
        }
        #id9 {
        text-align:right;
        border: 1px solid #ffffff;
        font-size:8;
        }
        .basic_table1_blank{
        border: 1px solid #ffffff;
        border-collapse: collapse;
        font-size:5;
        }
        .basic_table1_blank td{
        border: 1px solid #ffffff;
        }
        .basic_table1{
        text-align:center;
        border:1px solid black;
        border-collapse: collapse;
        }
        .basic_table1_white{
        text-align:center;
        border:1px solid black;
        border-collapse: collapse;
        border-top-color:#ffffff;
        }
        .basic_table1 td {
        border:1px solid black;
        font-size:2;
        }
        .basic_table1_white td {
        border:1px solid black;
        border-top-color:#ffffff;
        font-size:2;
        }
    </style>
</head>
<body>

<!--    <br/><br/>
    <table class="basic_table1_blank" width="730">
        <tr>
            <td id="id7" width="30">LINE</td>
            <td id="id7" width="230">
                 <table class="basic_table1_blank" width="230">
                            <tr>
                                <td width="230" height="10px" id="id8"><p align="center">DESCRIPTION</p></td>
                            </tr>
                            <tr>
                                <td height="10px" width="160" id="id8"><p align="left">PART ID<br/>VENDOR PART ID</p></td>
                                <td height="10px" width="35" id="id8">DWG REV</td>
                                <td height="10px" width="35" id="id8">ECN</td>
                            </tr>
                </table>
            </td>
            <td id="id7" width="80">
                <table class="basic_table1_blank" width="80">
                            <tr>
                                <td height="10px" width="40" id="id8">CO ACCOUNT JOB</td>
                                <td height="10px" width="40" id="id8">DEPT ID</td>
                            </tr>
                </table>
            </td>
            <td id="id7" width="60">DELIVERY DATE</td>
            <td id="id7" width="100">ORDER QUANTITY<br/>BALANCE DUE</td>
            <td id="id7" width="30">U/M</td>
            <td id="id7" width="100">UNIT PRICE<br/>EXTENDED PRICE</td>
            <td id="id7" width="60">
                 <table class="basic_table1_blank" width="70">
                            <tr>
                                <td width="60" id="id8">TAX CODE</td>
                            </tr>
                            <tr>
                                <td height="10px" width="40" id="id8">DISC %</td>
                                <td height="10px" width="30" id="id8">VAT</td>
                            </tr>
                </table>
            </td>
        </tr>
    </table>-->
    <br/>
    %for so in objects :
    <table class="basic_table1_blank" width="1000">
        %for line in so.order_line:
        <tr>
            <td id="id8" height="30px" width="40">${helper.get_increment_val(so.order_line,line) or ''|entity}</td>
            <td id="id8" width="310"><p align="left">${line.product_id.default_code or ''|entity}<br/>${line.name or ''|entity}</p></td>
            <td id="id8" width="130"></td>
            <td id="id8" width="60"></td>
            <td id="id8" width="120">${line.product_uom_qty or ''}</td>
            <td id="id8" width="50">${line.product_uom.name or ''|entity}</td>
            <td id="id8" width="100">${ line.price_unit or ''}</td>
            <td id="id8" width="90">
                <table class="basic_table1_blank" width="90">
                    %for o in line.tax_id:
                    <tr>
                        <td id="id8">${(o.amount) * 100 or '0.00'}%</td>
                    </tr>
                    %endfor
                </table>
            </td>
        </tr>
        %endfor
    </table>
     <br/><br/><br/><br/>
     <table class="basic_table1_blank" width="1000">
         <tr>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="70">
                            <tr>
                                <td height="10px" id="id1">SUBTOTAL</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b>${so.amount_untaxed or ''}</b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="30">
                 <table class="basic_table1_blank" width="30">
                            <tr>
                                <td height="10px" id="id1">DISC %</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b> </b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="100">
                            <tr>
                                <td height="10px" id="id1">ORDER DISC AMOUNT</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b> </b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="100">
                            <tr>
                                <td height="10px" id="id1">ORDER TAX AMOUNT</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b>${so.amount_tax or ''}</b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="100">
                            <tr>
                                <td height="10px" id="id1">ORDER TAX AMOUNT 2</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b>${so.amount_tax or ''}</b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="100">
                            <tr>
                                <td height="10px" id="id1">ORDER TAX AMOUNT 3</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b> </b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="100">
                            <tr>
                                <td height="10px" id="id1">ORDER VAT AMOUNT</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b> </b></font></td>
                            </tr>
                </table>
             </td>
             <td id="id7" width="100">
                 <table class="basic_table1_blank" width="100">
                            <tr>
                                <td height="10px" id="id1">ORDER TOTAL</td>
                            </tr>
                            <tr>
                                <td height="10px" id="id1"><font size="1.2px"><b>${so.amount_total or ''}</b></font></td>
                            </tr>
                </table>
             </td>
         </tr>
     </table>
     <br/><br/><br/>
     <table class="basic_table1_blank" width="1000">
         <tr>
             <td height="10px" width="550" id="id9">AUTHORIZED BY:</td>
             <td height="10px" width="350" id="id5"><font size="1.2px"><b> </b></font></td>
         </tr>
    </table>
    %endfor
</body>
</html>