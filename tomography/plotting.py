import os
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display
from ipywidgets import IntSlider, Checkbox, Button, Layout, HBox, interactive_output


class DataViewer(object):
    def __init__(self, slc_list, phase_list, kz_list, slc_stack, phase_stack, kz_stack):
        """
        functionality for displaying the input data (SLC, topographic phase and wave number)

        Parameters
        ----------
        slc_list: list
            a list containing the names of the SLC input files
        phase_list: list
            a list containing the names of the topographic phase input files
        kz_list: list
            a list containing the names of the SLC input files
        slc_stack
        phase_stack
        kz_stack
        """
        self.slc_list = slc_list
        self.phase_list = phase_list
        self.kz_list = kz_list

        self.slc_stack = slc_stack
        self.phase_stack = phase_stack
        self.kz_stack = kz_stack

        # define some options for display of the widget box
        self.layout = Layout(
            display='flex',
            flex_flow='row',
            border='solid 2px',
            align_items='stretch',
            width='88%'
        )

        # define a slider for changing a plotted image
        self.slider = IntSlider(min=1, max=len(self.slc_list) - 1, step=1, continuous_update=False,
                                description='file number',
                                style={'description_width': 'initial'},
                                layout=self.layout)

        display(self.slider)

        self.fig = plt.figure(num='visualization of input data')
        # display of SLC amplitude
        self.ax1 = self.fig.add_subplot(131)
        # display of topographical phase
        self.ax2 = self.fig.add_subplot(132)
        # display of wave number
        self.ax3 = self.fig.add_subplot(133)

        # enable interaction with the slider
        out = interactive_output(self.onslide, {'h': self.slider})

        plt.tight_layout()

    def onslide(self, h):
        """
        a function to respond to slider value changes

        Parameters
        ----------
        h: int
            the slider value

        Returns: None
        -------

        """
        slc_name = os.path.basename(self.slc_list[h])
        phase_name = os.path.basename(self.phase_list[h - 1])
        kz_name = os.path.basename(self.kz_list[h - 1])
        self.ax1.set_title('SLC intensity: {}'.format(slc_name), fontsize=12)
        self.ax2.set_title('phase: {}'.format(phase_name), fontsize=12)
        self.ax3.set_title('wavenumber: {}'.format(kz_name), fontsize=12)
        # logarithmic scaling of SLC amplitude
        amp_log = 10 * np.log10(np.absolute(self.slc_stack[:, :, h]))
        # computation if image percentiles for linear image stretching
        p02, p98 = np.percentile(amp_log, (2, 98))
        self.ax1.imshow(amp_log, cmap='gray', vmin=p02, vmax=p98)
        self.ax2.imshow(np.absolute(self.phase_stack[:, :, h]))
        self.ax3.imshow(np.absolute(self.kz_stack[:, :, h]))


class Tomographyplot(object):
    """
    functionality for creating the main tomography analysis plot
    """

    def __init__(self, capon_bf_abs, caponnorm):

        if not caponnorm.shape == capon_bf_abs.shape:
            raise RuntimeError('mismatch of input arrays')

        self.height = capon_bf_abs.shape[2] // 2
        self.capon_bf_abs = capon_bf_abs
        self.caponnorm = caponnorm
        #############################################################################################
        # widget box setup

        # define a slider for changing the horizontal slice image
        self.slider = IntSlider(min=-self.height, max=self.height, step=10, continuous_update=False,
                                description='inversion height',
                                style={'description_width': 'initial'})

        # a simple checkbox to enable/disable stacking of vertical profiles into one plot
        self.checkbox = Checkbox(value=True, description='stack vertical profiles')

        # a button to clear the vertical profile plot
        self.clearbutton = Button(description='clear vertical plot')
        self.clearbutton.on_click(lambda x: self.init_vertical_plot())

        # define some options for display of the widget box
        layout = Layout(
            display='flex',
            flex_flow='row',
            border='solid 2px',
            align_items='stretch',
            width='88%'
        )

        # display the widget box
        form = HBox([self.slider, self.checkbox, self.clearbutton], layout=layout)
        display(form)
        #############################################################################################
        # main plot setup

        # set up the subplot layout
        self.fig = plt.figure()
        # the horizontal slice plot
        self.ax1 = self.fig.add_subplot(221)
        # the vertical profile plot
        self.ax2 = self.fig.add_subplot(222)
        # the range slice plot
        self.ax3 = self.fig.add_subplot(413)
        # the azimuth slice plot
        self.ax4 = self.fig.add_subplot(414)
        plt.subplots_adjust(left=0.1, right=0.2, top=0.3, bottom=0.2)

        # set up the plots for range and azimuth slices
        self.ax3.set_xlim(0, capon_bf_abs.shape[1])
        self.ax4.set_xlim(0, capon_bf_abs.shape[0])

        # set up the y-axis ticks and labeling for the azimuth and range slice plots
        ytick_lab = [-self.height, -self.height // 2, 0, self.height // 2, self.height]
        ytick_pos = [0, self.height / 2, self.height, self.height + self.height / 2, self.height * 2]
        plt.setp([self.ax3, self.ax4], yticklabels=ytick_lab, yticks=ytick_pos)

        # set up the vertical profile plot
        self.init_vertical_plot()

        # add a cross-hair to the horizontal slice plot
        self.lhor = self.ax1.axhline(0, linewidth=1, color='r')
        self.lver = self.ax1.axvline(0, linewidth=1, color='r')

        # make the figure respond to mouse clicks by executing function onclick
        self.cid1 = self.fig.canvas.mpl_connect('button_press_event', self.onclick)

        # enable interaction with the slider
        out = interactive_output(self.onslide, {'h': self.slider})
        #############################################################################################
        # general formatting

        # format the cursor value displays
        self.ax1.format_coord = lambda x, y: 'range={0}, azimuth={1}, reflectivity='.format(int(x), int(y))
        self.ax2.format_coord = lambda x, y: 'reflectivity={0:.3f}, height={1}'.format(x, int(y))
        self.ax3.format_coord = lambda x, y: 'range={0}, height={1}, reflectivity='.format(int(x), int(y - self.height))
        self.ax4.format_coord = lambda x, y: 'range={0}, height={1}, reflectivity='.format(int(x), int(y - self.height))

        # arrange the subplots to make best use of space
        plt.tight_layout(pad=1.0, w_pad=0.1, h_pad=0.1)
        #############################################################################################

    def reset_crosshair(self, range, azimuth):
        """
        redraw the cross-hair on the horizontal slice plot
        Parameters
        ----------
        range: int
            the range image coordinate
        azimuth: int
            the azimuth image coordinate
        Returns: None
        -------

        """
        self.lhor.set_ydata(azimuth)
        self.lver.set_xdata(range)
        plt.draw()

    def init_vertical_plot(self):
        """
        set up the vertical profile plot
        Returns: None
        -------

        """
        # clear the plot if lines have already been drawn on it
        if len(self.ax2.lines) > 0:
            self.ax2.cla()
        # set up the vertical profile plot
        self.ax2.set_ylabel('height [m]', fontsize=12)
        self.ax2.set_xlabel('reflectivity', fontsize=12)
        self.ax2.set_title('vertical point profiles', fontsize=12)
        self.ax2.set_ylim(-self.height, self.height)

    def onslide(self, h):
        """
        a function to respond to slider value changes by redrawing the horizontal slice plot

        Parameters
        ----------
        h: int
            the slider value
        Returns: None
        -------

        """
        p1 = self.ax1.imshow(self.caponnorm[:, :, self.height - h], origin='upper', cmap='jet')
        self.ax1.set_xlabel('range', fontsize=12)
        self.ax1.set_ylabel('azimuth', fontsize=12)
        self.ax1.set_title('horizontal slice at height {} m'.format(h), fontsize=12)
        # remove the previous plot and its color bar
        if len(self.ax1.images) > 1:
            self.ax1.images[0].colorbar.remove()
            del self.ax1.images[0]
        cbar = self.fig.colorbar(p1, ax=self.ax1)
        cbar.ax.set_ylabel('reflectivity', fontsize=12)  # , rotation=270
        plt.show()

    def onclick(self, event):
        """
        respond to mouse clicks in the plot
        This function responds to clicks on the first (horizontal slice) plot and updates the vertical profile and
        slice plots

        Parameters
        ----------
        event: the click event object containing image coordinates

        Returns: None
        -------

        """
        # only do something if the first plot has been clicked on
        if event.inaxes == self.ax1:

            # retrieve the click coordinates
            rg = int(event.xdata)
            az = int(event.ydata)

            # redraw the cross-hair
            self.reset_crosshair(rg, az)

            # subset the tomography arrays
            subset_vertical = self.capon_bf_abs[az, rg, :]
            subset_range = self.caponnorm[az, :, :]
            subset_azimuth = self.caponnorm[:, rg, :]

            # redraw/clear the vertical profile plot in case stacking is disabled
            if not self.checkbox.value:
                self.init_vertical_plot()

            # plot the vertical profile
            label = 'rg: {0:03}; az: {1:03}'.format(rg, az)
            self.ax2.plot(np.flipud(subset_vertical), range(-self.height, self.height + 1), label=label)
            self.ax2_legend = self.ax2.legend(loc=0, prop={'size': 7}, markerscale=1)

            # plot the range slice
            self.ax3.imshow(np.rot90(subset_range, 1), origin='lower', cmap='jet', aspect='auto')
            self.ax3.set_title('range slice at azimuth line {}'.format(az), fontsize=12)

            # plot the azimuth slice
            self.ax4.imshow(np.rot90(subset_azimuth, 1), origin='lower', cmap='jet', aspect='auto')
            self.ax4.set_title('azimuth slice at range line {}'.format(rg), fontsize=12)