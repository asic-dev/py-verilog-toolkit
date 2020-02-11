
module pg_netlist(in1, in2, out1, out2, VDD_DIG, VSS_DIG);
  input in1;
  input in2;
  
  output out1;
  output out2;

  input VDD_DIG;
  input VSS_DIG;
  
  NOR _001_ (
    .A(in1),
    .B(in2),
    .Y(out1),
    .VDD(VDD_DIG),
    .VSS(VSS_DIG)
  );
  
  NOR _002_ (
    .A(in1),
    .B(in2),
    .Y(out2),
    .VDD(VDD_DIG),
    .VSS(VSS_DIG)
  );

endmodule
