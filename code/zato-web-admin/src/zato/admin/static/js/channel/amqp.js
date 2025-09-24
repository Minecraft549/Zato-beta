
// /////////////////////////////////////////////////////////////////////////////

$.fn.zato.data_table.ChannelAMQP = new Class({
    toString: function() {
        var s = '<ChannelAMQP id:{0} name:{1}>';
        return String.format(s, this.id ? this.id : '(none)', this.name ? this.name : '(none)');
    }
});

// /////////////////////////////////////////////////////////////////////////////

$(document).ready(function() {
    $('#data-table').tablesorter();
    $.fn.zato.data_table.class_ = $.fn.zato.data_table.ChannelAMQP;
    $.fn.zato.data_table.new_row_func = $.fn.zato.channel.amqp.data_table.new_row;
    $.fn.zato.data_table.parse();
    $.fn.zato.data_table.setup_forms(['name', 'address', 'username', 'password', 'queue', 'pool_size', 'service', 'prefetch_count']);
})

$.fn.zato.channel.amqp.create = function() {
    $.fn.zato.data_table._create_edit('create', 'Create a new AMQP channel', null);
}

$.fn.zato.channel.amqp.edit = function(id) {
    $.fn.zato.data_table._create_edit('edit', 'Update the AMQP channel', id);
}

$.fn.zato.channel.amqp.data_table.new_row = function(item, data, include_tr) {
    var row = '';

    if(include_tr) {
        row += String.format("<tr id='tr_{0}' class='updated'>", item.id);
    }

    var is_active = item.is_active == true;
    var cluster_id = $(document).getUrlParam('cluster');

    row += "<td class='numbering'>&nbsp;</td>";
    row += "<td class='impexp'><input type='checkbox' /></td>";
    row += String.format('<td>{0}</td>', item.name);
    row += String.format('<td style="text-align:center">{0}</td>', is_active ? 'Yes' : 'No');
    row += String.format('<td style="text-align:center">{0}</td>', item.address || '');
    row += String.format('<td style="text-align:center">{0}</td>', item.username || '');
    row += String.format('<td style="text-align:center">{0}</td>', item.queue);
    row += String.format('<td style="text-align:center">{0}</td>', $.fn.zato.data_table.service_text(item.service, cluster_id));
    row += String.format('<td>{0}</td>', String.format("<a href=\"javascript:$.fn.zato.channel.amqp.edit('{0}')\">", item.id) + "Edit</a>");
    row += String.format('<td>{0}</td>', String.format("<a href='javascript:$.fn.zato.channel.amqp.delete_({0});'>Delete</a>", item.id));
    row += String.format("<td class='ignore item_id_{0}'>{0}</td>", item.id);
    row += String.format("<td class='ignore'>{0}</td>", is_active);

    if(include_tr) {
        row += '</tr>';
    }

    return row;
}

$.fn.zato.channel.amqp.delete_ = function(id) {
    $.fn.zato.data_table.delete_(id, 'td.item_id_',
        'AMQP channel `{0}` deleted',
        'Are you sure you want to delete AMQP channel [{0}]?',
        true);
}
