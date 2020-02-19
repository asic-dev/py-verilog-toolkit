
test_suite:
	./pvt.py -ni test_data/pg_netlist.v \
	         -l test_data/ls.lib \
		 -m pg_netlist \
		 --export_upf test.upf

