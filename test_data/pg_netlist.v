
module pg_netlist(in1, in2, out1, out2, VDD, VSS);
  input in1;
  input in2;
  
  output out1;
  output out2;

  input VDD;
  input VSS;

  NOR _001_ (
    .A(in1),
    .B(in2),
    .Y(out1),
    .VDD(VDD),
    .VSS(VSS)
  );
  
  NOR _002_ (
    .A(in1),
    .B(in2),
    .Y(out2),
    .VDD(VDD),
    .VSS(VSS)
  );

endmodule
