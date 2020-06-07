/* -*- c++ -*- */
/*
 * Copyright 2020 gr-sandia_utils author.
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "compute_stats_impl.h"
#include <gnuradio/io_signature.h>
#include <volk/volk.h>

namespace gr {
namespace sandia_utils {

compute_stats::sptr compute_stats::make()
{
    return gnuradio::get_initial_sptr(new compute_stats_impl());
}


/*
 * The private constructor
 */
compute_stats_impl::compute_stats_impl()
    : gr::block("compute_stats", io_signature::make(0, 0, 0), io_signature::make(0, 0, 0))
{
    message_port_register_in(pmt::mp("pdu_in"));
    set_msg_handler(pmt::mp("pdu_in"),
                    boost::bind(&compute_stats_impl::handle_pdu, this, _1));
    message_port_register_out(PMT_PDU_OUT);
}

/*
 * Our virtual destructor.
 */
compute_stats_impl::~compute_stats_impl() {}

void compute_stats_impl::handle_pdu(pmt::pmt_t pdu)
{
    pmt::pmt_t meta;
    pmt::pmt_t v_data;

    // make sure PDU data is formed properly
    if (pmt::is_uniform_vector(pdu) && pmt::is_c32vector(pdu)) {
        meta = pmt::make_dict();
        v_data = pdu;
    } else {
        if (!(pmt::is_pair(pdu)))
            return;

        /* code */
        meta = pmt::car(pdu);
        v_data = pmt::cdr(pdu);

        if (!pmt::is_c32vector(v_data))
            return;
    }

    const std::vector<gr_complex> input = pmt::c32vector_elements(v_data);
    uint32_t v_len = input.size();

    float energy_sum = 0;
    std::vector<float> mag2(v_len, 0);
    volk_32fc_magnitude_squared_32f(&mag2[0], &input[0], v_len);
    volk_32f_accumulator_s32f(&energy_sum, &mag2[0], v_len);

    float power = 10 * log10(energy_sum / v_len);

    meta = pmt::dict_add(meta, PMT_ENERGY, pmt::from_double(energy_sum));
    meta = pmt::dict_add(meta, PMT_POWER, pmt::from_double(power));
    message_port_pub(PMT_PDU_OUT, pmt::cons(meta, v_data));
}

} /* namespace sandia_utils */
} /* namespace gr */
